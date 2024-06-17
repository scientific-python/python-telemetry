from api_tracer import install, setup_collector

if __name__ == "__main__":
    install(
        [
            "scipy.stats._distn_infrastructure"
        ]
    )
    setup_collector("scipy-service")

    from scipy import stats

    stats.norm.pdf(x=1, loc=1, scale=0.01)
    stats.norm(loc=1, scale=0.01).pdf(1)
