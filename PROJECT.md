# K8s Application Repo

**Deployment Engineer Take-Home Project - Time Estimate: 2-4 hrs.**

We are excited to have you participate in our take-home interview project. We want to be mindful of your time during this interview process, and have attempted to select something you will likely be experienced with based on your background. We have also divided the project into Core and Stretch deliverables. You should only care to bother with the Stretch Deliverables as your time permits. A submission with only the core deliverables will still be considered complete.

## Description

In this project, we would like you to showcase your skills and experience with various IaC tools, as well as your understanding of CI/CD tools. As such we would like you to create a repository in a public git repository service like Github (Gitlab or others are also acceptable) which will contain everything necessary to deploy a simple hello world application in Kubernetes, as well as the Kubernetes cluster itself.

We also would like you to showcase your technical communication skills by providing a README.md which explains how to deploy the application, for a minimally-technical audience.

## Goals

* Create a new repository with all necessary Infrastructure-as-Code components
* Setup CI/CD tooling the repository
* Demonstrate familiarity with Helm Charts
* Demonstrate familiarity with Terraform
* Demonstrate technical communication skills towards a minimally technical audience

## Deliverables

### Core Deliverables

**A custom Helm Chart for a simple "Hello, World!" application**
* This application does not need to do anything aside from run.
* Any sample application of your choice is fine too.

**Terraform code in a version control repository (e.g., GitHub or GitLab) to create the infrastructure and deploy the application.**
* Must create a Kubernetes cluster using the provider of your choice (Amazon EKS, Google Kubernetes Engine, Azure Kubernetes Service, Digital Ocean… etc.)
* It is not necessary for Terraform to install the Helm Chart

**CI/CD Automation for applying the Infrastructure-as-Code and installing the application**
* Use CI/CD that best fits the Repository host of your choice (Github Actions, Gitlab CI, etc.)
* Should at least apply the Terraform and Install the Helm Chart into the cluster.

**README.md which explains to minimally technical users how to deploy the application.**

**NOTE:** It is NOT necessary for you to deploy this into real infrastructure on your own. We may attempt to deploy it into our own infrastructure.

### Stretch Deliverables

* Your CI/CD can produce artifacts for distribution of your Application/Infrastructure-as-Code
* Write your own minimalist application to have Helm install
  * Include the application code in the repo and have your CI/CD build it.
* Use a Bitnami Chart as a subchart of your Helm chart.
  * Simply demonstrate that you know how to use it as a subchart of your helm chart, your chart can simply wrap around the subchart)
* Support multiple IaaS/Cloud Providers
* Tests/Validation of any kind

---

For any questions or concerns, please do not hesitate to reach out to ronits@comet.com

Good luck!

---

*comet.com*
*228 Park Ave S, Suite 15549 • New York, NY • 10003-1502 US*
*Yigal Alon 114, 13th FL • Tel Aviv, Israel*
*support@comet.ml*
