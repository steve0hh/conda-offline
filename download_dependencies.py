import requests
import sys
import os
import argparse
import logging

from conda_build import api as conda_api

logging.basicConfig(level=logging.INFO, format='%(message)s')

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# Adpated from - https://stackoverflow.com/a/16696317
def download_file(path, url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(os.path.join(path,local_filename), 'wb') as f:
        logger.debug("Writing to: %s", os.path.join(path,local_filename))
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-env", help="environment file path", type=str, default="requirements.txt")
    parser.add_argument("-channel", help="channel", type=str, default="main")
    parser.add_argument("-platform", help="platform you are building for", type=str, default="linux-64")
    parser.add_argument("-download-dir", help="platform you are building for", type=str, default="downloads")
    args = parser.parse_args()

    env_file_path = os.path.join(BASE_DIR, args.env)

    logger.debug("Environment file path %s", env_file_path)

    if not os.path.exists(env_file_path):
        logger.error(f"{env_file_path} does not exists!")
        sys.exit(1)

    download_path = os.path.join(args.download_dir, "channels", "linux-64")

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if not os.listdir(download_path):
        logger.warning("The path `%s` is not empty, will overwrite the directory packages")

    repo_url = "/".join(["https://repo.continuum.io/pkgs", args.channel, args.platform])
    index_url = "/".join([repo_url, "repodata.json"])

    logger.debug("Download url: %s", repo_url)
    logger.debug("Index url: %s", index_url)

    logger.info("********************************************************************************")

    logger.info("Downloading packages...")
    logger.info("Please be patient...")

    with open(env_file_path, 'r') as env_file_handle:
        # ignore commented lines and empty lines
        pkgs = [l[:-1] for l in env_file_handle.readlines() if l[0] != "#" or len(l) <= 1]

        for i, pkg in enumerate(pkgs):
            package_name = pkg.replace("=", "-") + ".tar.bz2"
            package_url = repo_url + "/" + package_name
            logger.debug("Downloading %s", package_url)
            download_file(download_path, package_url)

            # show progress bar
            sys.stdout.write('\r')
            sys.stdout.write("[%-40s] %d%%" % ('='*int(((i+1)/len(pkgs))*40), ((i+1)/len(pkgs))*100))
            sys.stdout.flush()

        sys.stdout.write('\n')
        sys.stdout.flush()

    logger.info("Creating channels indexes")

    conda_api.update_index(os.path.join(download_path, ".."))

    logger.info("Done!")

    logger.info("Script exited successfully!")

    sys.exit(0)
