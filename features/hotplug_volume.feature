@vm
Feature: Hotplug PVC to running VM
    As a Kubernetes administrator,
    I want to hotplug PVC to running VM,
    So that I can use the PVC as storage.

    Background: some requirement of this test
        Given 1 VM
        And 1 PVC

    Scenario: Hotplug PVC to running VM
        When I create the VM
        And I create the PVC
        Then the VM status should change to Running
        And the PVC status should change to Bound
        When I hotplug the PVC to the running VM
        Then the PVC should be successfully attached to the VM
        And the VM should detect the new storage device
        When I perform a deletion of the VM
        Then the VM should be completely removed
