pipeline {
    agent {
        kubernetes {
            yaml """
kind: Pod
metadata:
  name: demoPod
spec:
  nodeName: k8s-worker01
  dnsPolicy: Default
  containers:
  - name: kubectl
    namespace: jenkins
    image: bitnami/kubectl:latest
    imagePullPolicy: Always
    command:
    - /bin/sh
    tty: true
    securityContext:
      runAsUser: 0
  volumes:
  - name: jenkins-docker-cfg
    namespace: jenkins
    projected:
      sources:
      - secret:
          name: registry-credentials
          items:
            - key: .dockerconfigjson
              path: config.json
"""
        }
    }
    environment {
        REPOSITORY  = 'jang1023'
        IMAGE       = 'fastapi'
    }
    stages {
        stage('Build Docker image') {
            steps {
                script {
                    sh "docker build -t ${REPOSITORY}/${IMAGE}:${GIT_COMMIT} -f Dockerfile . --platform=linux/amd64"
                }
            }
        }
        stage('Approval'){
          steps{
            slackSend(color: '#FF0000', message: "Please Check Deployment Approval (${env.JOB_URL})")
            timeout(time: 15, unit:"MINUTES"){
              input message: 'Do you want to approve the deployment?', ok:'YES'
            }
          }
        }
        stage('Deploy kubernetes ') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        container('kubectl') {
                            sh """
                            export KUBECONFIG=\$KUBECONFIG
                            kubectl set image deployment/fastapi-app fastapi-app=${REPOSITORY}/${IMAGE}:${GIT_COMMIT} -n demo
                            kubectl rollout restart deployment/fastapi-app -n demo
                            """
                        }
                    }
                }
            }
        }
    }
}
