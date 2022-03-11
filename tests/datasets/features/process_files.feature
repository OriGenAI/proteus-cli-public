Feature: Process file uploads
    Background:
        Given a source url
        And a bucket url
        And a cases url
        And a tqdm instance
        And a set of cases
        And a number of workers
        And a process mock
        And a tqdm mock
        And a description mock
        And a refresh mock
        And setted up mocks

    Scenario: Process file uploads
        When I process files with workflow <workflow>
        Then Is it <called_process_mock> that I called the process_step method
        Then Is it <called_tqdm_mock> that I called the update_with_report method
        Then Is it <called_description_mock> that I called the set_description method
        Then Is it <called_refresh_mock> that I called the refresh method

        Examples:
            | workflow  | called_process_mock| called_tqdm_mock| called_description_mock| called_refresh_mock|
            |        hm |               True |            True |                   True |               True |
            |   cnn-pca |              False |           False |                  False |              False |
    
    Scenario: Process file uploads with an unknown workflow
        Then It throws a KeyError when workflow is fail