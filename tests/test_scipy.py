from api_tracer import install, start_span_processor

if __name__ == "__main__":
    install(
        [
            "scipy.stats._distn_infrastructure"
        ]
    )
    start_span_processor("scipy-service")

    from scipy import stats

    stats.norm.pdf(x=1, loc=1, scale=0.01)
    stats.norm(loc=1, scale=0.01).pdf(1)
