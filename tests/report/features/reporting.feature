Feature: Generate a report
    Scenario: Log info message
        Given a reporting instance
        When I log the messsage: logging some info
        Then I get a stdout message with: logging some info

    Scenario: Log error message
        Given a reporting instance
        When I log the error messsage: logging an error
        Then I get a stderr message with: logging an error

    Scenario: Log info message with abstract
        When (abstract) I log the messsage: logging some info
        Then I get a stdout message with: logging some info

    Scenario: Log error message with abstract
        When (abstract) I log the error messsage: logging an error
        Then I get a stderr message with: logging an error