Feature: PersistentVolumeClaim Snapshot via external-snapshotter
  As a Kubernetes administrator,
  I want to create, verify, and delete PVC snapshots

  Background:
    Given create a VolumeSnapshotClass

  @positive
  Scenario: Create and verify snapshot of a PVC
    Given a PVC "pvc-test" exists with size "1Gi" and access mode "ReadWriteOnce"
    When I create a snapshot from the PVC
    Then the snapshot should be created and have the status "ReadyForUse"
    And I delete the snapshot
    Then the snapshot should not exist

  @negative
  Scenario: Snapshot creation failure when PVC does not exist
    Given a PVC "non-existent-pvc" does not exist
    When I attempt to create a snapshot from the PVC
    Then an error should be raised indicating that the PVC does not exist
