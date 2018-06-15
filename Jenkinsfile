#!groovy

def default_channel_name = '#ci-cd'

def CHANNEL_NAME = env.CHANNEL_NAME == null ? default_channel_name : env.CHANNEL_NAME

def projectProperties = [
  buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '30', numToKeepStr: '100')),
  [$class: 'RebuildSettings', autoRebuild: false, rebuildDisabled: false],
  parameters(
    [
        string(      defaultValue: 'master',       description: 'The branch to target', name: 'BRANCH_NAME'),
        string(      defaultValue: CHANNEL_NAME,       description: 'The slack channel to use', name: 'CHANNEL_NAME'),
    ]
  ),
]

properties(projectProperties)

@Library('juiceinc-library') _

pipeline {
  agent  { label 'python-ecs' }
  stages {
    stage('Checkout') {
      steps{
        sendNotifications('STARTED', "$CHANNEL_NAME")
        checkout scm
      }
    }

    stage('Installing Prereqs') {
      steps {
        sh '''
#!/usr/bin/bash
virtualenv --no-site-packages .venv
. .venv/bin/activate
pip install -qq -U pip wheel
pip install -qq --exists-action w -r requirements.txt
pip install -qq --exists-action w -r jbcli/requirements-dev.txt
'''
      }
    }
    stage('Linting') {
      steps {
        sh '''
#!/usr/bin/bash
. .venv/bin/activate
echo "flake8">> flake8_errors.txt
flake8 --output-file=flake8_errors.txt --exit-zero . '''
      }
    }
    stage('Testing') {
      steps {
        sh '''
#!/usr/bin/bash
. .venv/bin/activate
cd jbcli
pytest --junit-xml=junit.xml --cov-branch --cov-report=xml --cov=jbcli/cli
'''
      }
    }
    stage('Build and Publish Docs') {
      steps {
        sh '''
#!/usr/bin/bash
. .venv/bin/activate
export AWS_SECURITY_TOKEN=`echo $AWS_SESSION_TOKEN`
cd jbcli
make docs
aws s3 sync docs/_build/html s3://internal.juiceboxdata.com/projects/jbcli --acl bucket-owner-full-control --delete
'''
      }
    }

  }
post {
    always {
      archiveArtifacts '**/flake8_errors.txt, **/junit.xml, **/coverage.xml'
      warnings canComputeNew: false, canResolveRelativePaths: false, canRunOnFailed: true, categoriesPattern: '', defaultEncoding: '', excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[parserName: 'Pep8', pattern: 'flake8_errors.txt']], unHealthy: ''
      junit 'jbcli/junit.xml'
      step([$class: 'CoberturaPublisher', autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: '**/coverage.xml', failUnhealthy: false, failUnstable: false, maxNumberOfBuilds: 0, onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false])
      sendNotifications(currentBuild.result, "$CHANNEL_NAME")
    }
  }
}
