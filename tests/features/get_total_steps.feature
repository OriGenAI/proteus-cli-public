Feature: Get total steps of a case
    Background:
        Given a list of cases
        And setting a mock for case details

    Scenario: Get total steps of a case
        When I get the total steps of cases with workflow <workflow>
        Then I should get <expected_steps> steps

        Examples:
            | workflow  | expected_steps|
            |        hm |            17 |
            |   cnn-pca |             4 |

    Scenario: Get total steps of a case with an unknown workflow
        Then It throws a KeyError when workflow is fail
