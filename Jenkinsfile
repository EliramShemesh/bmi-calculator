pipeline {
    agent any
    parameters {
        string(name: 'HEIGHT', defaultValue: '', description: 'Height in cm')
        string(name: 'WEIGHT', defaultValue: '', description: 'Weight in kg')
        string(name: 'USER', defaultValue: '', description: 'Slack user ID')
    }
    stages {
        stage('Run BMI Script') {
            steps {
                script {
                    def result = sh(script: "python3 bmi.py ${params.HEIGHT} ${params.WEIGHT}", returnStdout: true).trim()
                    echo "BMI result: ${result}"

                    // Send result to Slack backend
                    sh """
                    curl -X POST -H "Content-Type: application/json" \
                        -d '{"user": "${params.USER}", "bmi": "${result}"}' \
                        https://your-server-url/jenkins/result
                    """
                }
            }
        }
    }
}
