@vm
Feature: Node Management
    As a Kubernetes administrator,
    I want to manage node operations and validate VM migration,
    So that I can ensure VMs are correctly handled during node maintenance.

    Scenario: Drain node and migrate VM
        Given 1 migratable VM
        When  I create the VM
        Then  the VM status should change to Running
        And   I can access the VM
        When  I drain the node where the VM is running
        Then  the VM should migrate to another node
        And   the VM should be Running on the new node
