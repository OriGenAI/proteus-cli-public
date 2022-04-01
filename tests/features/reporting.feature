Feature: Generate a report
    Scenario: Send a report
        Given a mocked oidc module
        And a reporting instance
        When sending a report with message: reporting status
        Then the mocked api is called once
        And I get a message with: reporting status
    
    Scenario: Send a report without api instance
        Given a mocked oidc module
        And a reporting instance without api reference
        When sending a report with message: reporting status
        Then the mocked api is not called
        And I get a message with: reporting status

    Scenario: Log info message
        When I log the messsage: logging some info
        Then I get a message with: logging some info

    Scenario: Log error message
        When I log the error messsage: logging an error
        Then I get a message with: logging an error
