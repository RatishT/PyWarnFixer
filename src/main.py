from src.pywarnfixer import analyze, fetch, sample, setup
from src.pywarnfixer.fixes import fixes, fixes2


def main():
    # setup.setup_folders()
    # sample.sample_repositories()
    # fetch.fetch_repositories()
    # analyze.analyze()
    # fixes.auto_fix()
    fixes2.auto_fix()
    # setup.delete_repos()


if __name__ == "__main__":
    main()
