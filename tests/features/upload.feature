Feature: Upload dataset to bucket
    Scenario: Upload dataset to bucket
        Given a bucket
        And a dataset uuid
        And a mocked tqdm wraper
        When I upload a dataset
        Then there are logged messages
        And the file is uploaded
