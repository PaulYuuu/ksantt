@vm
Feature: VirtualMachine Creation
    As a Kubernetes administrator,
    I want to validate VM operations with various configurations,
    So that I can ensure proper virtualization management in the cluster.

    Scenario: Create and verify VM with basic configuration
        Given a VM specification with 2 vCPUs and 4Gi memory
        When I create the VM
        Then the VM status should change to Running
        When I perform a deletion of the VM
        Then the VM should be completely removed
