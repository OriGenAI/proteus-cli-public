Feature: Process file uploads
    Background:
        Given a source url
        And a bucket url
        And a cases url
        And a tqdm instance
        And a number of workers
        And a tqdm mock
        And a description mock
        And a refresh mock
        And a keywords mock

    Scenario: Process file uploads
        Given a process mock
        And setted up mocks
        And a set of cases
        When I process files with workflow <workflow>
        Then Is it <called_process_mock> that I called the process_step method
        Then Is it <called_tqdm_mock> that I called the update_with_report method
        Then Is it <called_description_mock> that I called the set_description method
        Then Is it <called_refresh_mock> that I called the refresh method

        Examples:
            | workflow  | called_process_mock| called_tqdm_mock| called_description_mock| called_refresh_mock|
            |        hm |               True |            True |                   True |               True |
            |   cnn-pca |               True |            True |                   True |               True |
    
    Scenario: Process cnn-pca files
        Given a bucket mock
        And a download mock
        And a temporary dir mock
        And a dataset get mock
        And setted up mocks for cnn-pca
        And a set of cases without split
        When I process cnn-pca files
        Then the bucket mock is called
        And the preprocessed files are created

    Scenario: Process file uploads with an unknown workflow
        Given a process mock
        And setted up mocks
        And a set of cases
        Then It throws a KeyError when workflow is fail