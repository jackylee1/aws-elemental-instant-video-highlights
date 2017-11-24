# Instant video highlights: build your own Live-to-VOD workflow with machine-learning image recognition

Demonstration of a frame accurate live-to-VOD solution with automatic machine-learning image recognition Introduction to the AWS services used to create the demonstration Explanation of how the services were combined to create a solution

Then… your turn! Create this service by yourself

Why add frame accurate clipping to AWS Elemental Delta if segment clipping already works? 

Remove non-relevant content: previous ad, previous scene… straight to the point

Reduce time to post (social media era: first post wins all!)

## Overall solution workflow

![](images/catfinder5000-workflow.png)

## Demo of the service: what it can do

### Website Preview

![](images/catfinder5000-preview.png)

### Gotta Catch them All

What do people like to watch on the internet?

![](images/catfinder5000-cat.png)

In this lab, you will be creating the "Catfinder-5000"! Which was a name I chose to ensure no one has made any S3 bucket names that could conflict. The name "catfinder-5000" also clearly states that it finds cats. ( an the 5000 just makes it more fun to say ) The code currently only matches the Rekognition label "Cat", but can be overridden to any label of your choosing.

## AWS Services used under the hood

![](images/catfinder5000-overall.png)

## re:Invent Workshop

Start here: Module 0 [re:Invent Workshop Start](0_reInventWorkshop/README.md )

## Module Listing

Module 0: [re:Invent Workshop Start](0_reInventWorkshop/README.md )

Module 1: [S3 Static Web hosting](1_StaticWebHosting/README.md)

Module 2: [DynamoDB and Lambda](2_DynamoDB/README.md)

Module 3: [Lambda and Delta](3_Lambda/README.md)

Module X: [Extra Credit](X_ExtraCredit/README.md) 
( Not required, but you will learn more things! )

Module Z: [Clean Up](Z_CleanUp/README.md) 
( Highly recommended to complete so you won't have unnecessary AWS charges )
