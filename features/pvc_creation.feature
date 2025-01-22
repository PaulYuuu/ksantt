@pvc
Feature: PVC Creation
    As a Kubernetes administrator,
    I want to validate PVC operations with various storage configurations,
    So that I can ensure proper data persistence and access control in the cluster.

    Scenario Outline: Create and verify PVC
        Given a PVC specification with access mode <accessModes> and storage mode <volumeMode>
        When  I create the PVC
        Then  the PVC status should change to Bound
        When  I perform a deletion of the PVC
        Then  the PVC should be completely removed

        Examples:
            | accessModes     | volumeMode  |
            | ReadWriteOnce   | Block       |
            | ReadOnlyMany    | Block       |
            | ReadWriteMany   | Block       |
            | ReadWriteOnce   | Filesystem  |

        @negative
        Examples:
            | accessModes     | volumeMode  |
            | ReadOnlyMany    | Filesystem  |
            | ReadWriteMany   | Filesystem  |
