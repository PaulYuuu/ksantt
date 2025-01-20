@vm
Feature: Multiple VMs with multiple volumes
    As a Kubernetes administrator,
    I want to create multiple VMs with multiple volumes,
    So that I can test the VMs functionality.

    Background: Multiple VMs
        Given 2 VMs
            | disk_type |
            | virtio    |
            | scsi      |

    Scenario: Create multiple VMs
        When I create the VMs
        Then the VMs status should change to Running
        And  I can access the VMs
        When I perform a deletion of the VMs
        Then the VMs should be completely removed
