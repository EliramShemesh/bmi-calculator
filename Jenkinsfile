pipeline {
    agent any

    // Parameters sent from Slack via buildWithParameters
    parameters {
        string(name: 'HEIGHT', defaultValue: '', description: 'Height in cm')
        string(name: 'WEIGHT', defaultValue: '', description: 'Weight in kg')
        string(name: 'USER', defaultValue: '', description: 'Slack user ID')
    }

    // Inject secrets from Jenkins Credentials Store
    environment {
        // These IDs must match your Jenkins credentials entries
        SLACK_BOT_TOKEN = credentials('SLACKBOT_TOKEN')
        FLASK_RESULT_URL = credentials('FLASK_RESULT_URL') // if you stored it as a secret
    }

    stages {
        stage('Setup') {
            steps {
                echo "Starting BMI calculation for user: ${params.USER}"
                // Optional: create venv, install dependencies
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -q requests
                '''
            }
        }

        stage('Run BMI Script') {
            steps {
                script {
                    echo "Calculating BMI for height: ${params.HEIGHT} and weight: ${params.WEIGHT}"
                    // Run your BMI Python script and capture result
                    def bmi = sh(
                        script: ". venv/bin/activate && python3 bmi.py ${params.HEIGHT} ${params.WEIGHT}",
                        returnStdout: true
                    ).trim()

                    echo "BMI result: ${bmi}"

                    // Post result to Flask backend (which will post to Slack)
                    sh """
                        curl -s -X POST -H "Content-Type: application/json" \
                        -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
                        -d '{
                            "user": "${params.USER}",
                            "bmi": "${bmi}"
                        }' \
                        ${FLASK_RESULT_URL}
                    """
                }
            }
        }
    }

    post {
        failure {
            echo "BMI calculation failed for user ${params.USER}"
            sh """
                curl -s -X POST -H "Content-Type: application/json" \
                -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
                -d '{
                    "user": "${params.USER}",
                    "bmi": "Error: Jenkins job failed"
                }' \
                ${FLASK_RESULT_URL}
            """
        }
    }
}
