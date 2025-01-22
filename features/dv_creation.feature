@dv
Feature: DV Creation
    As a Kubernetes administrator,
    I want to validate DV operations with various storage configurations,
    So that I can ensure proper data persistence and access control in the cluster.

    Scenario Outline: Create and verify DV
        Given a DV with access mode <accessModes> and volume mode <volumeMode>
        When  I create the DV
        Then  the DV status should change to Succeeded
        When  I perform a deletion of the DV
        Then  the DV should be completely removed

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
