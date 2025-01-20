@vm
Feature: Hotplug volumes to running VM
    As a Kubernetes administrator,
    I want to hot plug/unplug volumes to running VM,
    So that I can test the volumes hotplug/unplug functionality.

    Background: 1 basic VM
        Given 1 VM

    Scenario Outline: Hotplug PVCs to running VM
        Given <pvcs> PVCs
        When  I create the VM
        And   I create the PVCs
        Then  the VM status should change to Running
        And   the PVCs status should change to Bound
        When  I hotplug <pvcs> PVCs to the running VM
        Then  the VM should be able to access the new PVCs
        When  I perform a deletion of the VM
        Then  the VM should be completely removed

        Examples:
            | pvcs |
            | 1    |
            | 2    |
            | 8    |
