Feature: Upload dataset to bucket
    Scenario: Upload dataset to bucket
        Given a bucket
        And a dataset uuid
        And a set of mocks
        When I upload a dataset
        Then there are logged messages
        And the files are uploaded
