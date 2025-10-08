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
        SLACK_BOT_TOKEN = credentials('SLACKBOT_TOKEN')
        FLASK_RESULT_URL = credentials('FLASK_RESULT_URL')
    }

    stages {
        stage('Setup') {
            steps {
                echo "Preparing environment..."
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -q requests flask python-dotenv
                '''
            }
        }

        stage('Start Flask') {
            steps {
                echo "Starting Flask server in background..."
                sh '''
                    . venv/bin/activate
                    SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN}" \
                    JENKINS_URL="${JENKINS_URL}" \
                    JENKINS_USER="${JENKINS_USER}" \
                    JENKINS_TOKEN="${JENKINS_TOKEN}" \
                    nohup python3 main.py > flask.log 2>&1 &
                    sleep 5
                    '''
    }
}

        stage('Calculate BMI') {
            steps {
                script {
                    echo "Calculating BMI for HEIGHT=${params.HEIGHT} WEIGHT=${params.WEIGHT}"

                    // Simple BMI calculation in Jenkins (Python one-liner)
                    def bmi = sh(
                        script: """
                            . venv/bin/activate
                            python3 -c "h=float('${params.HEIGHT}'); w=float('${params.WEIGHT}'); print(round(w/((h/100)**2), 2))"
                        """,
                        returnStdout: true
                    ).trim()

                    echo "BMI result: ${bmi}"

                    // Post result to Flask backend (which will forward to Slack)
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
