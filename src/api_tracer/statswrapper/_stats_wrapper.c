// Copyright (c) 2025 Scientific Python. All rights reserved.

#include <Python.h>
#include "structmember.h"


typedef struct {
    PyObject *kwname;
    PyObject *known_params;
    Py_ssize_t count;
    Py_ssize_t *param_counts;
} arginfo;


typedef struct {
    PyObject_VAR_HEAD
    vectorcallfunc vectorcall;
    PyObject *wrapped;
    PyObject *dict;
    Py_ssize_t total_calls;
    Py_ssize_t invalid_args;
    Py_ssize_t error_results;
    Py_ssize_t npos;
    Py_ssize_t npos_only;
    arginfo args[];  // NULL terminated arguments (one more with no kwname).
} StatsWrapperObject;


static inline int
handle_arg_stats(arginfo *arginfo, PyObject *arg)
{
    arginfo->count++;

    if (arginfo->known_params != NULL) {
        Py_ssize_t n_params = PyTuple_GET_SIZE(arginfo->known_params);
        Py_ssize_t idx = 0;
        for (; idx < n_params; idx++) {
            if (PyTuple_GET_ITEM(arginfo->known_params, idx) == arg) {
                break;
            }
        }
        if (idx == n_params) {
            idx = 0;
            for (; idx < n_params; idx++) {
                int eq = PyObject_RichCompareBool(
                    PyTuple_GET_ITEM(arginfo->known_params, idx), arg, Py_EQ);

                if (eq < 0) {
                    if (PyErr_ExceptionMatches(PyExc_RecursionError) ||
                            PyErr_ExceptionMatches(PyExc_MemoryError) ||
                            PyErr_ExceptionMatches(PyExc_KeyboardInterrupt)) {
                        return -1;
                    }
                    // Just ignore all but the most critical errors here...
                    PyErr_Clear();
                }
                if (eq) {
                    break;
                }
            }
        }
        if (idx != n_params) {
            arginfo->param_counts[idx]++;
        }
    }
    return 0;
}


static PyObject *
statswrapper_vectorcall(StatsWrapperObject *self,
        PyObject *const *args, Py_ssize_t len_args, PyObject *kwnames)
{
    int invalid_args = 0;
    Py_ssize_t nargs = PyVectorcall_NARGS(len_args);

    /* Make sure we don't crash on bad args (or incorrect setup) */
    Py_ssize_t nargs_valid = nargs;
    if (nargs > self->npos) {
        invalid_args = 1;
        nargs_valid = self->npos;
    }

    for (Py_ssize_t i = 0; i < nargs_valid; i++) {
        if (handle_arg_stats(&self->args[i], args[i]) < 0) {
            return NULL;
        }
    }

    Py_ssize_t nkwargs = kwnames ? PyTuple_GET_SIZE(kwnames) : 0;
    for (Py_ssize_t i = 0; i < nkwargs; i++) {
        PyObject *kwname = PyTuple_GET_ITEM(kwnames, i);
        PyObject *arg = args[nargs + i];

        arginfo *curr_arginfo = self->args + self->npos_only;
        // Fast identity check, should always work out if the user told us all
        // possible kwargs.
        while (curr_arginfo->kwname != NULL) {
            if (curr_arginfo->kwname != kwname) {
                curr_arginfo++;
                continue;
            }
            break;
        }
        if (curr_arginfo->kwname == NULL) {
            /* The fast path didn't work out (UNLIKELY may make sense here) */
            curr_arginfo = self->args + self->npos_only;
            while (curr_arginfo->kwname != NULL) {
                int eq = PyObject_RichCompareBool(curr_arginfo->kwname, kwname, Py_EQ);
                if (eq < 0) {
                    /* Should never happen, so error out right here */
                    return NULL;
                }
                if (eq) {
                    break;
                }
                curr_arginfo++;
            }
        }
        /* If kwname is still NULL, we are not tracking it! */
        if (curr_arginfo->kwname != NULL) {
            if (handle_arg_stats(curr_arginfo, arg) < 0) {
                return NULL;
            }
        }
        else {
            invalid_args = 1;
        }
    }

    self->total_calls++;
    self->invalid_args = self->invalid_args + invalid_args;
    PyObject *res = PyObject_Vectorcall(self->wrapped, args, len_args, kwnames);
    if (res == NULL) {
        self->error_results++;
    }
    return res;
}


static PyObject *
statswrapper__get_counts(StatsWrapperObject *self, PyObject *unused)
{
    return Py_BuildValue("nnn", self->total_calls, self->error_results, self->invalid_args);
}


static PyObject *
statswrapper__get_param_stats(StatsWrapperObject *self, PyObject *unused)
{
    PyObject *res = PyTuple_New(Py_SIZE(self) - 1);
    if (res == NULL) {
        return NULL;
    }
    for (Py_ssize_t i = 0; i < Py_SIZE(self) - 1; i++) {
        PyObject *known_params = self->args[i].known_params;
        PyObject *param_counts;
        if (known_params == NULL) {
            known_params = Py_None;
            Py_INCREF(Py_None);
            param_counts = Py_None;
        }
        else {
            Py_ssize_t n_known_params = PyTuple_GET_SIZE(known_params);
            param_counts = PyTuple_New(n_known_params);
            if (param_counts == NULL) {
                Py_DECREF(res);
                return NULL;
            }
            for (Py_ssize_t j = 0; j < n_known_params; j++) {
                PyObject *count = PyLong_FromSsize_t(self->args[i].param_counts[j]);
                if (count == NULL) {
                    Py_DECREF(res);
                    Py_DECREF(param_counts);
                    return NULL;
                }
                PyTuple_SET_ITEM(param_counts, j, count);
            }
        }
        PyObject *item = Py_BuildValue("OnON",
            self->args[i].kwname ? self->args[i].kwname : Py_None,
            self->args[i].count, known_params, param_counts);
        if (item == NULL) {
            Py_DECREF(res);
            return NULL;
        }
        PyTuple_SET_ITEM(res, i, item);
    }
    return res;
}


static PyObject *
statswrapper__set_npos(StatsWrapperObject *self, PyObject *arg)
{
    Py_ssize_t npos = PyLong_AsSsize_t(arg);
    if (npos == -1 && PyErr_Occurred()) {
        return NULL;
    }
    if (npos < self->npos_only || npos > Py_SIZE(self) - 1) {
        PyErr_SetString(PyExc_ValueError,
                "invalid new value for npos for the function.");
    }
    self->npos = npos;
    Py_RETURN_NONE;
}


static void
statswrapper_dealloc(StatsWrapperObject *self)
{
    Py_DECREF(self->wrapped);
    for (Py_ssize_t i = 0; i < Py_SIZE(self) - 1; i++) {
        Py_XDECREF(self->args[i].kwname);
        Py_XDECREF(self->args[i].known_params);
        PyMem_Free(self->args[i].param_counts);
    }
    PyObject_FREE(self);
}


static PyObject *
statswrapper___get__(PyObject *self, PyObject *obj, PyObject *cls)
{
    if (obj == NULL) {
        /* Act like a static method, no need to bind */
        Py_INCREF(self);
        return self;
    }
    return PyMethod_New(self, obj);
}


static struct PyGetSetDef statswrapper_getset[] = {
    {"__dict__", &PyObject_GenericGetDict, 0, NULL, 0},
    {0, 0, 0, 0, 0}
};


static PyMethodDef statswrapper_methods[] = {
    {"_get_counts",
        (PyCFunction)statswrapper__get_counts,
        METH_NOARGS, NULL},
    {"_get_param_stats",
        (PyCFunction)statswrapper__get_param_stats,
        METH_NOARGS, NULL},
    {"_set_npos",
        (PyCFunction)statswrapper__set_npos,
        METH_O, NULL},
    {NULL, NULL, 0, NULL}
};


static PyTypeObject StatsWrapper_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "stats_wrapper._StatsWrapper",
    .tp_basicsize = sizeof(StatsWrapperObject),
    .tp_itemsize = sizeof(arginfo),
    .tp_dealloc = (destructor)statswrapper_dealloc,
    // TODO: We should plausibly traverse dict and `wrapped`.  This doesn't
    //       matter for non-dynamic functions in practice.
    .tp_flags = (Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_VECTORCALL),
    .tp_call = &PyVectorcall_Call,
    .tp_vectorcall_offset = offsetof(StatsWrapperObject, vectorcall),
    .tp_dictoffset = offsetof(StatsWrapperObject, dict),
    .tp_descr_get = statswrapper___get__,
    .tp_getset = statswrapper_getset,
    .tp_methods = statswrapper_methods,
};


/*
 * Factory for the StatsWrapper object creation.
 */
static PyObject *
stats_wrapper_create(PyObject *mod,
        PyObject *const *args, Py_ssize_t len_args, PyObject *kwnames)
{
    Py_ssize_t nargs = PyVectorcall_NARGS(len_args);
    if (nargs < 1) {
        PyErr_SetString(PyExc_TypeError, "Must pass at least one callable.");
        return NULL;
    }
    /* Store the wrapped one, and treat all other arguments as generic args */
    PyObject *wrapped = args[0];
    args++;
    nargs--;

    Py_ssize_t total_args = nargs;
    if (kwnames != NULL) {
        total_args += PyTuple_GET_SIZE(kwnames);
    }
    StatsWrapperObject *statswrapper = (StatsWrapperObject *)PyObject_NewVar(
        StatsWrapperObject, &StatsWrapper_Type, total_args + 1);
    if (statswrapper == NULL) {
        return NULL;
    }

    statswrapper->vectorcall = (vectorcallfunc)statswrapper_vectorcall;
    statswrapper->npos_only = nargs;
    // Allow setting the number of positional args (i.e. enforce kwarg only).
    statswrapper->npos = total_args;
    statswrapper->total_calls = 0;
    statswrapper->error_results = 0;
    statswrapper->invalid_args = 0;
    // Ensure we can dealloc and also NULL terminate.
    memset(statswrapper->args, 0, sizeof(arginfo) * (total_args + 1));

    Py_INCREF(wrapped);
    statswrapper->wrapped = wrapped;
    statswrapper->dict = PyDict_New();
    if (statswrapper->dict == NULL) {
        Py_DECREF(statswrapper);
        return NULL;
    }

    for (Py_ssize_t i = 0; i < total_args; i++) {
        if (i >= nargs) {
            statswrapper->args[i].kwname = PyTuple_GET_ITEM(kwnames, i - nargs);
            Py_INCREF(statswrapper->args[i].kwname);
            /* should be interned, but lets make sure */
            PyUnicode_InternInPlace(&statswrapper->args[i].kwname);
        }
        if (args[i] == Py_None) {
            continue;
        }
        if (!PyTuple_Check(args[i])) {
            PyErr_SetString(PyExc_TypeError,
                "All arguments must be None, or tuples.");
            Py_DECREF(statswrapper);
            return NULL;
        }
        /* The typical case: We have a tuple with values to check for. */
        Py_INCREF(args[i]);
        statswrapper->args[i].known_params = args[i];
        size_t num = PyTuple_GET_SIZE(args[i]);
        statswrapper->args[i].param_counts = PyMem_Calloc(num, sizeof(Py_ssize_t));
        if (statswrapper->args[i].param_counts == NULL) {
            Py_DECREF(statswrapper);
            return PyErr_NoMemory();
        }
    }

    return (PyObject *)statswrapper;
}


static struct PyMethodDef module_methods[] = {
    {"stats_wrapper", (PyCFunction)stats_wrapper_create,
        METH_FASTCALL | METH_KEYWORDS, "StatsWrapper creation helper"},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef moduledef = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "_stats_wrapper",
    .m_methods = module_methods
};


PyMODINIT_FUNC PyInit__stats_wrapper(void)
{
    PyObject *m = PyModule_Create(&moduledef);

    if (PyType_Ready(&StatsWrapper_Type) < 0) {
        goto error;
    }
    if (PyModule_AddObject(m, "_StatsWrapper", (PyObject *)&StatsWrapper_Type) < 0) {
        goto error;
    }

    return m;
  error:
    Py_DECREF(m);
    return NULL;
}
