@pvc
Feature: PersistentVolumeClaim Creation
  As a Kubernetes administrator,
  I want to ensure that PVCs can be created, verified, and deleted
  with different access and volume modes.

  Scenario Outline: Create and delete PVC
    Given a PVC with accessMode <accessModes> and volumeMode <volumeMode>
    When I create a PVC
    Then the PVC should be Bound
    When I delete the PVC
    Then the PVC should not exist

    Examples:
      | accessModes     | volumeMode  |
      | ReadWriteOnce   | Block       |
      | ReadOnlyMany    | Block       |
      | ReadWriteMany   | Block       |
      | ReadWriteOnce   | Filesystem  |
      | ReadOnlyMany    | Filesystem  |
      | ReadWriteMany   | Filesystem  |
