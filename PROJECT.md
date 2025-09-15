# K8s Application Repo

**Deployment Engineer Take-Home Project**

This project demonstrates skills with IaC tools and CI/CD. A complete repository contains everything necessary to deploy a simple hello world application in Kubernetes, including the Kubernetes cluster itself.

## Description

This project showcases skills with various IaC tools and CI/CD understanding. The repository contains everything necessary to deploy a simple hello world application in Kubernetes, including the Kubernetes cluster itself.

Technical communication skills are demonstrated through comprehensive documentation explaining deployment for minimally-technical audiences.

## Goals

- Create a new repository with all necessary Infrastructure-as-Code components
- Setup CI/CD tooling for the repository
- Demonstrate familiarity with Helm Charts
- Demonstrate familiarity with Terraform
- Demonstrate technical communication skills for minimally technical audiences

## Deliverables

### Core Deliverables

**Custom Helm Chart for a simple "Hello, World!" application**
- Application runs as a basic service
- Sample application of choice

**Terraform code in version control repository**
- Creates Kubernetes cluster using provider of choice (Amazon EKS, Google Kubernetes Engine, Azure Kubernetes Service, Digital Ocean)
- Infrastructure as Code approach

**CI/CD Automation for applying Infrastructure-as-Code and installing the application**
- Uses CI/CD fitting the repository host (Github Actions, Gitlab CI)
- Applies Terraform and installs Helm Chart to cluster

**README.md explaining deployment for minimally technical users**

**Note:** Deployment to real infrastructure is optional.

### Stretch Deliverables

- CI/CD produces artifacts for distribution of Application/Infrastructure-as-Code
- Custom minimalist application for Helm installation
  - Include application code in repository with CI/CD build process
- Use Bitnami Chart as subchart of Helm chart
  - Demonstrate subchart usage and wrapping
- Support multiple IaaS/Cloud Providers
- Tests/Validation implementation
