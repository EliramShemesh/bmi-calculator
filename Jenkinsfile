pipeline {
    agent any
    parameters {
        string(name: 'Height', defaultValue: '', description: 'User height in meters')
        string(name: 'Weight', defaultValue: '', description: 'User weight in kg')
    }
    stages {
        stage('Calculate BMI') {
            steps {
                script {
                    // Check out your repository where the python script resides
                    checkout scm

                    // Execute the python script, passing the parameters
                    sh "python your_bmi_script.py --height ${params.HEIGHT} --weight ${params.WEIGHT}"
                }
            }
        }
        // Optional: Add a stage to send the BMI result back to Slack
        // using the slackSend step (requires Slack Notification Plugin).
    }
}