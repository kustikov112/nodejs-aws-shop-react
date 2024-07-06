from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
)
from constructs import Construct

class CdkDeploymentStack(Stack):

    def __init__(self, scope: Construct, constructor_id: str, **kwargs) -> None:
        super().__init__(scope, constructor_id, **kwargs)

        file_bucket = s3.Bucket.from_bucket_name(self, "ExistingBucket", "task-5-bucket-for-shop-csv")

        site_bucket = s3.Bucket(self, "rs-module2-kustikov-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=True)
        
        oai = cloudfront.OriginAccessIdentity(self, "OAI_new",
            comment="OAI for my distribution"
        )        


        distribution = cloudfront.Distribution(self, "MyStaticSiteDistribution",
                                               default_behavior=cloudfront.BehaviorOptions(
                                                   origin=origins.S3Origin(site_bucket, origin_access_identity=oai),
                                                   viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                                                   allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL
                                               ),
                                                
                                                default_root_object="index.html")

        
        site_bucket.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[site_bucket.arn_for_objects("*")],
            principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
            conditions={
                "StringEquals": {
                    "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
                }
            }
        ))

        # file_bucket.add_to_resource_policy(iam.PolicyStatement(
        #     actions=["s3:*"],
        #     resources=[site_bucket.arn_for_objects("*")],
        #     principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")]
        # ))

        site_bucket.grant_read(oai)
        # file_bucket.grant_put(oai)



        s3deploy.BucketDeployment(self, "DeployWithInvalidation",
            sources=[s3deploy.Source.asset("../dist")],
            destination_bucket=site_bucket,
            distribution=distribution,
            distribution_paths=["/*"]
        )
