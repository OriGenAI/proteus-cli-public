Feature: Process file uploads
    Background:
        Given a source url
        And a bucket url
        And a cases url
        And a tqdm instance
        And a number of workers

    Scenario: Process file uploads
        Given a set of cases
        When I process files with workflow <workflow>
        Then Is it <called_process_mock> that I called the process_step method
        Then Is it <called_tqdm_mock> that I called the update_with_report method
        Then Is it <called_description_mock> that I called the set_description method
        Then Is it <called_refresh_mock> that I called the refresh method

        Examples:
            | workflow  | called_process_mock| called_tqdm_mock| called_description_mock| called_refresh_mock|
            |        hm |               True |            True |                   True |               True |
            |   cnn-pca |               True |            True |                   True |               True |
    
    Scenario: Process file uploads with an unknown workflow
        Given a set of cases
        Then It throws a KeyError when workflow is fail