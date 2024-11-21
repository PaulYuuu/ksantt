Feature: DataVolume Creation
  As a Kubernetes administrator,
  I want to ensure that DataVolumes can be created, verified, and deleted
  with different access and volume modes.

  Scenario Outline: Create and delete DataVolume
    Given a DataVolume with accessModes <accessModes> and volumeMode <volumeMode>
    When I create a DataVolume
    Then the DataVolume should be Succeeded
    When I delete the DataVolume
    Then the DataVolume should not exist

    Examples:
      | accessModes     | volumeMode  |
      | ReadWriteOnce   | Block       |
      | ReadOnlyMany    | Block       |
      | ReadWriteMany   | Block       |
      | ReadWriteOnce   | Filesystem  |
      | ReadOnlyMany    | Filesystem  |
      | ReadWriteMany   | Filesystem  |
