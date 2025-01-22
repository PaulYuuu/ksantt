@vm
Feature: VM Migration
    As a Kubernetes administrator,
    I want to migrate the VM,
    So that I can ensure proper virtualization management in the cluster.

    Scenario: Migrate VM
        Given 1 migratable VM
        When  I create the VM
        Then  the VM status should change to Running
        And   I can access the VM
        When  I migrate the VM
        When  I perform a deletion of the VM
        Then  the VM should be completely removed

    Scenario Outline: Migrate VM with multiple volumes
        Given 1 migratable VM with <count> <vl_type>

        Examples:
            | count | vl_type    |
            | 2     | PVC        |
            | 8     | DataVolume |
