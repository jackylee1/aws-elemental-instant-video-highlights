# Instant video highlights: build your own Live-to-VOD workflow with machine-learning image recognition

Demonstration of a frame accurate live-to-VOD solution with automatic machine-learning image recognition Introduction to the AWS services used to create the demonstration Explanation of how the services were combined to create a solution

Then… your turn! Create this service by yourself

Why add frame accurate clipping to AWS Elemental Delta if segment clipping already works? 

Remove non-relevant content: previous ad, previous scene… straight to the point

Reduce time to post (social media era: first post wins all!)

## Overall solution workflow

Since we are indexing a live stream, we have to keep in mind this has perpetually run. We don't have the luxury of running a single long running running process through a video and be completed. So we will break this up into sections for easier understanding to see how each one of the Live to VOD clips are generated.

![](images/catfinder5000-workflow.png)

1. The "Live Stream Conversion" is utilizing AWS Elemental Cloud PaaS for both AWS Elemental Live and AWS Elemental Delta.

1. The "Content Processing" is utilizing AWS Services to index the livestream created by AWS Elemental products. Read more: [parse lambda](catfinder5000-parse/README.md )

1. The "Content Clipping" is utlizing AWS Services to talk to AWS Elemental Delta to create a Live to VOD archive. Read more: [prekog lambda](catfinder5000-prekog/README.md )

1. The "Asset Playback" is utlizing a static Website hosted in S3 with javascript to dynamically create a dashboard. Read more: [website](catfinder5000-website/README.md )

## AWS Services used under the hood

![](images/catfinder5000-overall.png)

### Website Preview

Below is what you will see after completing all the modules. This lab will utilize a static website to see the results of your backend processes working in realtime.

![](images/catfinder5000-preview.png)

### Gotta Catch them All

What do people like to watch on the internet? We will use a lot of technology to create cat videos.

![](images/catfinder5000-cat.png)

In this lab, you will be creating the "Catfinder-5000"! Which was a name I chose to ensure no one has made any S3 bucket names that could conflict. The name "catfinder-5000" also clearly states that it finds cats. ( an the 5000 just makes it more fun to say ) The code currently only matches the Rekognition label "Cat", but can be overridden to any label of your choosing.

## re:Invent Workshop

Start here: Module 0 [re:Invent Workshop Start](0_reInventWorkshop/README.md )

### Module Listing

Module 0: [re:Invent Workshop Start](0_reInventWorkshop/README.md )

Module 1: [S3 Static Web hosting](1_StaticWebHosting/README.md)

Module 2: [DynamoDB](2_DynamoDB/README.md)

Module 3: [Lambda](3_Lambda/README.md)

Module X: [Extra Credit](X_ExtraCredit/README.md) ( Not required, but you will learn more things! )

Module Z: [Clean Up](Z_CleanUp/README.md) ( Highly recommended to complete so you won't have unnecessary AWS charges )
