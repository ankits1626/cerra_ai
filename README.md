# Rewardz AI




This is code for ai related microservices.
Technologies used:

- Fast API
- Docker


## Development
### Local development with docker

- install docker client
- create an `.env` file in project root
    #### Sample ENV file

    ```
    DATA_PATH=data
    # database related 
    DB_USER=xxxxx
    DB_PASSWORD=xxxxx
    DB_HOST=db
    DB_PORT=5432
    DB_NAME=xxxxx
    #AWS
    OCR_AWS_REGION_NAME=xxxxxx
    OCR_AWS_ACCESS_KEY_ID=xxxxxxxx
    OCR_AWS_SECRET_ACCESS_KEY=xxxxxxxx
    ```
- run docker compose up
- access the microservice at http://localhost:8003
- view the api docs at http://localhost:8003/docs



### Without Docker
*TBD*

## Testing
-  create a virual enviornment and install dependencies
- pytest tests/ --log-cli-level=INFO (with logs)
-  pytest tests/

## Integration with Backend app
in `skor/settings/default.py` add following setting 

``AI_MICROSERVICE_CONFIG = {
      "BASE_URL": "http://x.x.x.x:8003"
}``

where `x.x.x.x` is the ip of the machine


## Deployment
*TBD*