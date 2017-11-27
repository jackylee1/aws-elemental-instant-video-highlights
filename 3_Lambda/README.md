# Module 3: AWS Lambda

In this module, you'll use AWS Lambda to analyze data in Amazon DynamoDB to trigger AWS Elemental Delta's API to create a Frame Accurate Live-to-VOD ( L2V ) that generates a MP4 video that can be played through the HTML5 player hosted on your S3 Static Website from Module 1.

You'll implement a Lambda function that will be invoked by an Amazon CloudWatch Event every minute. The function will parse the HLS manifest, process the transport stream video file with ffmpeg and ffprobe, upload images to Amazon S3, request label analysis from Amazon Rekognition, and record the results in a DynamoDB table.

The function is invoked from CloudWatch Events. You'll implement that connection in this module. The "parse" Lambda will invoke the "prekog" Lambda when certain criteria are met. The default behavior will be when a `Cat` label is found with Amazon Rekognition.

## Browser

We recommend you use the latest version of Chrome to complete this workshop. You may use the latest version of Firefox and Safari, but the video.js player may not operate correctly and you won't be able to play video.

## Create an IAM Role for your Lambda Function

### Background

Every Lambda function has an IAM role associated with it. This role defines what other AWS services the function is allowed to interact with. For the purposes of this workshop, you'll need to create an IAM role that grants your Lambda function permission to write logs to Amazon CloudWatch Logs and access the Amazon services utlized in this lab.

### High-Level Instructions - IAM

Use the IAM console to create a new role. Name it `CatFinderRole` and select AWS Lambda for the role type. You'll need to attach policies that grant your function permissions to write to Amazon CloudWatch Logs, access tables in DynamoDB, read and write to S3, invoke a AWS Lambda process, and allow Amazon Rekognition to access images files in your S3 bucket.

Attach the managed policy called `AWSLambdaBasicExecutionRole` to this role to grant the necessary CloudWatch Logs permissions. Also, create a custom inline policy for your role that allows the Lambda to access the DynamoDB Tables, Amazon S3 bucket, and Amazon Rekognition and invoke the `catfinder5000-prekog` Lambda you will set up in the next module.

### Step-by-step instructions - IAM

1. From the AWS Management Console, on the **Services** menu, click **IAM**.

1. In the left navigation pane, click **Roles** and then click **Create role**.

1. For **Select type of trusted entity**, click **AWS service**.

1. Under "Choose the service that will use this role", click **Lambda**.

    **Note:** Selecting a role type automatically creates a trust policy for your role that allows AWS services to assume this role on your behalf. If you were creating this role using the CLI, AWS CloudFormation or another mechanism, you would specify a trust policy directly.

1. Click **Next: Permissions**.

1. In **Search Filter**, type `AWSLambdaBasicExecutionRole` and check the box next to that role.

1. Click **Next: Review**.

1. For **Role name**, enter `CatFinderRole`

1. Select **Create role**.

1. In **Search**, type `CatFinderRole` and then select the role you just created.

1. On the **Permissions** tab, click **Add inline policy** at the bottom right.

1. Ensure **Custom Policy** is selected and then click **Select**.

1. For **Policy Name**, type `CatFinderPolicy`

1. For **Policy Document**, enter the following, replacing `[YOUR_BUCKET_NAME]` with the name of the bucket you created in section 1 and `YOUR_AWS_ACCOUNT` with your AWS account number:

    **Note:** Remove any `-` ( dashes ) in your account number for an ARN

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Stmt1508302425000",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:*"
                ],
                "Resource": [
                    "arn:aws:dynamodb:us-west-2:YOUR_AWS_ACCOUNT:table/catfinder5000-list",
                    "arn:aws:dynamodb:us-west-2:YOUR_AWS_ACCOUNT:table/catfinder5000-list/*",
                    "arn:aws:dynamodb:us-west-2:YOUR_AWS_ACCOUNT:table/catfinder5000-main",
                    "arn:aws:dynamodb:us-west-2:YOUR_AWS_ACCOUNT:table/catfinder5000-main/*",
                    "arn:aws:dynamodb:us-west-2:YOUR_AWS_ACCOUNT:table/catfinder5000-summary",
                    "arn:aws:dynamodb:us-west-2:YOUR_AWS_ACCOUNT:table/catfinder5000-summary/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    "arn:aws:s3:::YOUR_BUCKET_NAME/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "rekognition:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:*"
                ],
                "Resource": [
                    "arn:aws:lambda:us-west-2:YOUR_AWS_ACCOUNT:function:catfinder5000-parse",
                    "arn:aws:lambda:us-west-2:YOUR_AWS_ACCOUNT:function:catfinder5000-prekog"
                ]
            }
        ]
    }
    ```

1. Click **Validate Policy**.

    "Policy is valid" should appear above the Policy name or use the Warning/Error message to troubleshoot.

1. Click **Apply Policy**.

    You should now have a Role with 2 polices attached: 

    * AWSLambdaBasicExecutionRole

    * CatFinderPolicy

## 1. Create a Lambda Function - Parse

### Background - Parse Lambda

AWS Lambda will run your code in response to events such as a CloudWatch Event or an invocation from another Lambda. In this step, you'll build the core function that will parse the HLS manifest, process the transport stream video file into jpg images, utilize AWS Rekognition and update entries in Amazon DynamoDB. 

### High-Level Instructions - Parse Lambda

Use the AWS Lambda console to create a new Lambda function called `catfinder5000-parse` that will parse the HLS manifest and invoke another Lambda (that you will configure in the next Module). Use the provided [catfinder5000-parse](../catfinder5000-parse/README.md) implementation for your function code. In this lab, you will reference a zip file on a shared S3 location in this Module when creating your AWS Lambda function.

Make sure to configure your function to use the `CatFinderRole` IAM role you created in the previous section.

### Step-by-step instructions - Parse Lambda

1. Confirm you are in Oregon ( us-west-2 ) Region

1. On the **Services** menu, click **Lambda**.

1. Click **Create function**.

1. Click **Author from scratch**.

1. For **Name**, enter `catfinder5000-parse`.

1. For **Role**, confirm that **Choose existing role** is selected.

1. For **Existing role**, click **CatFinderRole**.

1. Click **Create function**.

1. On the "Configuration" tab, under "Function code," do the following:

    1. For **Code entry type**, click **Upload a file from Amazon S3** .

    1. For **Runtime**, click **Python 2.7**.

    1. For **Handler**, enter `lambda_function.lambda_handler`

        **Note:** you may have to choose "Upload a file from Amazon S3" in "Code entry type" again

    1. For **S3 link URL**, enter `https://s3-us-west-2.amazonaws.com/rodeolabz-us-west-2/instantvideohighlights/catfinder5000-parse.zip`

        **Note:** this zip file is the same code from the repo [catfinder5000-parse](../catfinder5000-parse/README.md) in a zip file for convinence of this lab.

1. Under **Environment variables**, enter the following:

    1. For **Key**, enter `HLS_URL` and then in **Value**, enter your HLS master manifest URL

        **Note:** Key and Value parameters do not have quotes

    1. For **Key**, enter `S3_BUCKET` and then in **Value**, enter `catfinder5000-firstname-lastname`

1. Under "Execution role", make sure the following selections are made (this should be filled out already):

    1. Leave **Choose existing role** on the first drop-down list.

    1. For **Existing Role**, click **CatFinderRole**.

1. Under **Basic Settings**, enter the following:

    * For **Memory:**, select **1024 MB**

    * For **Timeout:**, enter `2` min `0` sec

    * For **Description**, type `Ain't No Party Like a Cat Party`

1. Click **Save** at the top of the screen.

    **Note:** Do not Click "Save and Test" as we will "Test" in the next section

## Implementation Validation - Lambda

For this section, you will test the function that you built using the AWS Lambda console. Later, you will add a CloudWatch Event to trigger this on a regular interval. You'll run it once and make sure the configuration is correct.

### Step-by-step instructions - Validation

1. From the main edit screen for your function, click **Test** on the top right.

1. In the **Configure test event** dialog:

    * For **Event Template**, click **Hello World**.

    * For **Event Name**, enter `mytest`

    * Click **Create**.

1. Back in the main edit screen, click **Test**.

    **Note:** if the test is successful, it will run for 60 - 70 seconds.

1. Under **Execution result: succeeded**, click **Details** to verify that the execution was successful.

1. You should see `SUCCESS: it ran`

    **Note:** common configuration errors should return, otherwise you may need to use Cloudwatch Logs or the log preview in Lambda Console for better troubleshooting accuracy.

## Cloudwatch Event Trigger

Now that you have a valid Lambda, you need to add a Cloudwatch Event Trigger that will execute every minute.

### Step-by-step instructions - Cloudwatch Event

1. Click the **Triggers** tab.

1. Click **Add Trigger**.

1. Click the box to the left of the "Lambda" icon and then click **CloudWatch Events**.

1. For **Rule**, click **Create a new rule**.

1. For **Rule name**, enter `1minute`

1. For **Rule description**, enter `runs every 1 minute today only`

1. For **Rule type**, make sure that `Schedule expression` is selected.

1. For **Schedule expression**, enter `cron(* 17-23 27 11 ? 2017)`
    **Note:** this crontab expression will only work November 27, 2017 between the hours of 9am to 3pm PST

1. Make sure that **Enable trigger** is checked.

1. Click **Submit**.

## Cloudwatch Metrics and Logs

Now that you have this running on a one-minute interval, you need to monitor and make sure things are working correctly. From the **Monitoring** tab, you can look at how many invocations are happening and also be directly linked to the CloudWatch Logs. 

To "tail" the logs, follow these steps.

### Step-by-step instructions - Cloudwatch Logs

1. Click the **Monitoring** tab.

1. Click **View Logs in CloudWatch**.

1. Click **Search Log Group**.

1. Click **30s** to the right of **Filter Events**.

1. Periodically click the **Refresh** icon to get newest information.

From here, you can press the Refresh button or keep scrolling down to see the latest logs from the Lambda.

## 2. Create a Lambda Function - Prekog

### Background - Prekog

AWS Lambda will run your code in response to events such as CloudWatch Event or an invocation from another Lambda. In this step, you'll build the core function using the data collected from the previous `catfinder5000-parse` Lambda to get frame accurate parameters of when a cat was detected in AWS Rekognition.

### High-Level Instructions

Use the AWS Lambda console to create a new Lambda function called `catfinder5000-prekog` that will query the DynamoDB table to accurately choose time stamps of when a cat has appeared and is no longer on in video. You will take those parameters and submit an API request to the AWS Elemental Delta instance. Use the provided [catfinder5000-prekog](../catfinder5000-prekog/README.md) implementation for your function code. You will upload this zip file via the console when creating your Lambda.

Make sure to configure your function to use the `CatFinderRole` IAM role you created in the previous module.

### Step-by-step instructions

1. Confirm you are in Oregon ( us-west-2 ) Region

1. On the **Services** menu, click **Lambda**.

1. Click **Create function**.

1. Click **Author from scratch**.

1. For **Name**, enter `catfinder5000-prekog`

1. For **Role**, leave **Choose existing role** selected.

1. For **Existing role**, click **CatFinderRole**.

1. Click **Create function**.

1. On the "Configuration" tab, under "Function Code", do the following:

    1. For **Code entry type**, click **Upload a file from Amazon S3**.

    1. For **Runtime**, click **Python 2.7**.

    1. For **Handler**, enter `lambda_function.lambda_handler`

        **Note:** you may have to choose "Upload a file from Amazon S3" in "Code entry type" again

    1. For **S3 link URL**, enter `https://s3-us-west-2.amazonaws.com/rodeolabz-us-west-2/instantvideohighlights/catfinder5000-prekog.zip`

        **Note:** this zip file is the same code from the repo [catfinder5000-prekog](../catfinder5000-prekog/README.md) in a zip file for convinence of this lab.

1. Under **Environment variables**, enter the following:

    1. For **Key**, enter `DELTA_URL` and then for **Value** enter your team's AWS Elemental Delta service URL

    1. For **Key**, enter `DELTA_CONTENTNAME` and then for **Value** enter your AWS Elemental Delta Channel name

1. Under "Execution role", make sure the following selections are made (this should be filled out already):

    1. Leave **Choose existing role** on the first drop-down list.

    1. For **Existing Role**, click **CatFinderRole**.

1. Under **Basic Settings**, enter the following:

    * For **Memory:**, select **256 MB**

    * For **Timeout:**, enter `2` min `0` sec

    * For **Description**, type `Because A Cat Party Don't Stop`

1. Click **Save** at the top of the screen.

    **Note:** Do not Click "Save and Test" as we will "Test" in the next section

## 2. Implementation Validation - Watch It Work

Since this Lambda is being invoked from the `catfinder5000-parse`, bring up the webpage that is hosted in your Amazon S3 bucket static website and watch everything update in real time. We can now watch the final results of all your hard work.

1. Navigate to your website's base URL (this is the URL you noted in Module 1) in the browser of your choice. 

    **Note:** If you need to look up the base URL, visit the Amazon S3 console, select your bucket, and then click the **Static Web Hosting** card on the **Properties** tab.

1. Watch the website to see the process working as it updates dynamically every 10 seconds

1. Click the thumbnails of the videos on the far right column to invoke a HTML5 player to view the Live-to-VOD asset from AWS Elemental Delta.

## Extra Credit

If you finished this like way too fast... Then we have something extra for you to do that isn't required to make the Lab run, but is neat to learn. Continue on to Module X: [Extra Credit](../X_ExtraCredit/README.md) if you have extra time to spare and only work on the Module section you have completed so far.

## Finished! - Time to cleaup this mess

Now that you have completed the whole lab, it is time to clean up all the things we created in these modules. Please use the checklist here in Module Z: [Clean Up](../Z_CleanUp/README.md)