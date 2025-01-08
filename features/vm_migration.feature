@vm
Feature: VirtualMachine Migration
    As a Kubernetes administrator,
    I want to migrate the VM,
    So that I can ensure proper virtualization management in the cluster.

    Scenario: Migrate VM
        Given 1 migratable VM
        When I create the VM
        Then the VM status should change to Running
        And I can access the VM
        When I migrate the VM
        When I perform a deletion of the VM
        Then the VM should be completely removed
