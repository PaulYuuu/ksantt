@vm
Feature: VM Creation
    As a Kubernetes administrator,
    I want to ensure that VMs can be created, verified, and deleted
    with different access and volume modes.

    Scenario Outline: Create and delete VM
        Given a VM with 2 vCPUs and 4Gi memory
        When I create a VM
        Then the VM should be in Running phase
        When I delete the VM
        Then the VM should not exist
