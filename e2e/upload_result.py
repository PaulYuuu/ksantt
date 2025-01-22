import json
import os
import xml.etree.ElementTree as ET

import requests

RP_API_KEY: str | None = os.getenv("rp_api_key")
RP_ENDPOINT: str | None = os.getenv("rp_endpoint")
RP_PROJECT: str | None = os.getenv("rp_project")


def filter_skipped_tests(input_file: str) -> ET.Element:
    """
    Filters out skipped test cases from a JUnit XML file.

    Args:
        input_file (str): Path to the input JUnit XML file.

    Returns:
        ET.Element: The root of the filtered XML tree.
    """
    tree = ET.parse(input_file)
    root = tree.getroot()

    for testsuite in root.findall("testsuite"):
        testcases = testsuite.findall("testcase")
        for testcase in testcases:
            if testcase.find("skipped") is not None:
                testsuite.remove(testcase)

    return root


def upload_junit_to_rp(filtered_xml: ET.Element) -> None:
    """
    Uploads the filtered JUnit XML content to ReportPortal.

    Args:
        filtered_xml (ET.Element): The root of the filtered JUnit XML tree.
    """
    if not all([RP_API_KEY, RP_ENDPOINT, RP_PROJECT]):
        raise RuntimeError("Missing ReportPortal environment variables.")
    url = f"{RP_ENDPOINT}/api/v1/plugin/{RP_PROJECT}/junit/import"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {RP_API_KEY}",
    }

    launch_import_data = {
        "attributes": [
            {"key": "Kubernetes", "value": "e2e"},
            {"value": "Sanity"},
        ],
        "description": "Kubernetes E2E testing with kubesan.gitlab.io driver",
        "mode": "DEFAULT",
        "name": "Kubernetes E2E Testing",
    }

    filtered_xml_str = ET.tostring(filtered_xml, encoding="utf-8", method="xml")

    files = {
        # Fallback the filename as the launch name
        "file": ("Kubernetes E2E Testing.xml", filtered_xml_str, "text/xml"),
    }

    response = requests.post(url, headers=headers, files=files, data={"launchImportRq": json.dumps(launch_import_data)})

    if response.status_code == 200:
        print("JUnit result uploaded successfully!")
        result_url = f"{RP_ENDPOINT}/ui/#{RP_PROJECT}/launches/all/{response.json()['data']['id']}"
        print(f"Visit {result_url} to analyze results.")
    else:
        print(f"Failed to upload. Status Code: {response.status_code}, Response: {response.text}")


def main(source_file: str) -> None:
    """
    Main function to execute the full workflow:
    1. Filters out skipped test cases from the input JUnit XML file.
    2. Uploads the filtered XML content to ReportPortal.
    3. Retrieves and prints the launch URL.

    Args:
        source_file (str): The path to the source JUnit XML file.
    """
    # Step 1: Filter out skipped test cases
    filtered_xml = filter_skipped_tests(source_file)
    print("Filtered XML created.")

    # Step 2: Upload filtered junit result to ReportPortal
    upload_junit_to_rp(filtered_xml)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python script.py <source_file>")
        sys.exit(1)

    main(sys.argv[1])
