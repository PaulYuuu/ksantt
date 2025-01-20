@vm
Feature: VM Creation
    As a Kubernetes administrator,
    I want to validate VM operations with various configurations,
    So that I can ensure proper virtualization management in the cluster.

    Scenario: Create and verify VM
        Given 1 VM
        When  I create the VM
        Then  the VM status should change to Running
        And   I can access the VM
        When  I perform a deletion of the VM
        Then  the VM should be completely removed
