This Python application provides a web server that responds to Octopus subscriptions like `Deployment succeeded` and 
`Deployment failed` and writes the associated task logs to disk.

This project is intended to provide the glue between am external logging system and Octopus task logs. By having an
external logging agent watch for new log files, Octopus task logs can be ingested into almost any external logging
solution.