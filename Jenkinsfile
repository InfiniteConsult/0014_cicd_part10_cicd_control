pipeline {
    agent {
        label 'general-purpose-agent'
    }

    stages {
        stage('Setup & Build') {
            steps {
                echo '--- Building Project ---'
                sh 'python3.12 -m venv .venv && . .venv/bin/activate && python3 -m pip install .[test]'
            }
        }

        stage('Test & Coverage') {
            steps {
                echo '--- Running Tests ---'
                sh '. .venv/bin/activate && pytest --cov=src/cicd_control --cov-report=xml tests/'
            }
        }

        stage('Code Analysis') {
            steps {
                script {
                    def sonarProjectKey = sh(returnStdout: true, script: 'grep "^sonar.projectKey=" sonar-project.properties | cut -d= -f2').trim()
                    def sonarHostUrl = 'http://sonarqube.cicd.local:9000'
                    withSonarQubeEnv('SonarQube') {
                        sh 'sonar-scanner'
                    }
                    timeout(time: 4, unit: 'MINUTES') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            mattermostSend(
                                color: 'danger',
                                channel: 'engineering@alerts',
                                message: ":no_entry: **Quality Gate Failed**: ${qg.status}\n<${sonarHostUrl}/dashboard?id=${sonarProjectKey}|View Analysis>"
                            )
                            error "Pipeline aborted due to quality gate failure: ${qg.status}"
                        }
                    }
                }
            }
        }

        stage('Package'){
            steps {
                echo '--- Packaging Artifacts ---'
                sh 'mkdir -p dist'
                sh ". .venv/bin/activate && python3 -m build --sdist --wheel"
            }
        }

        stage('Publish') {
            steps {
                echo '--- Publishing to Artifactory ---'

                rtUpload(
                    serverId: 'artifactory',
                    spec: """{
                        "files": [
                            {
                                "pattern": "dist/*",
                                "target": "generic-local/cicd-control/${BUILD_NUMBER}/",
                                "flat": "true"
                            }
                        ]
                    }""",
                    failNoOp: true,
                    buildName: "${JOB_NAME}",
                    buildNumber: "${BUILD_NUMBER}"
                )

                rtPublishBuildInfo (
                    serverId: 'artifactory',
                    buildName: "${JOB_NAME}",
                    buildNumber: "${BUILD_NUMBER}"
                )
            }
        }
    }

    post {
        failure {
            mattermostSend (
                color: 'danger',
                message: ":x: **Build Failed**\n**Job:** ${env.JOB_NAME} #${env.BUILD_NUMBER}\n(<${env.BUILD_URL}|Open Build>)"
            )
        }
        success {
            mattermostSend (
                color: 'good',
                message: ":white_check_mark: **Build Succeeded**\n**Job:** ${env.JOB_NAME} #${env.BUILD_NUMBER}\n(<${env.BUILD_URL}|Open Build>)"
            )
        }
    }

}