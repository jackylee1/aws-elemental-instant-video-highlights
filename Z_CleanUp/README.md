# Cleanup Steps

## Most Important

Please remember to disable the CloudWatch Event for your `catfinder5000-parse`. Though it is configured to only run for the hours of this lab, it would be smart to disable it completely so you don't run up a large AWS bill. 

## Module 1 - S3 Bucket

1. In the AWS Management Console, choose **Services**, and then select **S3** under Storage.

1. Select your `catfinder5000-first-last` in the main listing 

    *Note:* you won't click the name, but to the space to the right of the name

1. Click **Delete Bucket**

## Module 2 - DynamoDB

1. Confirm you are in Oregon ( us-west-2 ) Region

1. From the AWS Management Console, on the **Services** menu, click **DynamoDB**.

1. Select your `catfinder5000-main` table from the list

1. Click **Delete Table** 

1. Repeat for `catfinder5000-summary` and `catfinder5000-list`

## Module 3 - IAM and Lambda

### IAM Instructions

1. From the AWS Management Console, on the **Services** menu, click **IAM**.

1. In the left navigation pane, click **Roles**

1. In **Search**, type `CatFinderRole` and Select by clicking the name

1. Click **Delete role**

### Lambda Instructions

1. Confirm you are in Oregon ( us-west-2 ) Region

1. On the **Services** menu, click **Lambda**.

1. In **Search**, type `catfinder5000`

1. Select by clicking the radio button to the left of the name `catfinder5000-parse`

1. Click **Actions**

1. Click **Delete**

1. Repeat process for `catinder5000-prekog`
