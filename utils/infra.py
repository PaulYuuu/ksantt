import platform
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
import urllib3
from kubernetes.dynamic import DynamicClient
from kubernetes.dynamic.exceptions import ResourceNotFoundError
from ocp_resources.console_cli_download import ConsoleCLIDownload


def get_console_spec_links(client: DynamicClient, name: str):
    """
    Get console specification links for a given client and name.
    """
    ccd = ConsoleCLIDownload(client=client, name=name)
    if ccd.exists:
        return ccd.instance.spec.links
    raise ResourceNotFoundError(f"{name} ConsoleCLIDownload not found")


def extract_binary_from_cluster(client, name):
    """
    Download binary from cluster and extract it to /usr/local/bin/.
    """
    dst_path = Path("/usr/local/bin")
    binary_map = {
        "helm": "helm-download-links",
        "oc": "oc-cli-downloads",
        "virtctl": "virtctl-clidownloads-kubevirt-hyperconverged",
    }

    console_cli_links = get_console_spec_links(client, binary_map[name])
    download_urls = [entry["href"] for entry in console_cli_links]
    os_system = platform.system().lower()
    os_system = "mac" if os_system == "darwin" and platform.mac_ver()[0] else os_system
    os_machine = "amd64" if (machine := platform.machine()) == "x86_64" else machine
    # FIXME: Remove SSL warning
    urllib3.disable_warnings()
    for url in download_urls:
        if os_system in url and os_machine in url:
            download_url = url
            break
    with TemporaryDirectory() as temp_dir:
        filename = Path(urlparse(download_url).path).name
        local_filename = Path(temp_dir) / filename
        with requests.get(url, verify=False, stream=True) as created_request:
            created_request.raise_for_status()
            with open(local_filename, "wb") as file:
                for chunk in created_request.iter_content(chunk_size=8192):
                    file.write(chunk)
        archive_file = ZipFile(local_filename) if local_filename.suffix == ".zip" else TarFile(local_filename)
        archive_file.extract(name, dst_path)

    return dst_path / name


def extract_helm_binary(client):
    """
    Extract Helm binary from cluster.
    """
    return extract_binary_from_cluster(client, "helm")


def extract_oc_binary(client):
    """
    Extract OpenShift CLI binary from cluster.
    """
    return extract_binary_from_cluster(client, "oc")


def extract_virtctl_binary(client):
    """
    Extract virtctl binary from cluster.
    """
    return extract_binary_from_cluster(client, "virtctl")
