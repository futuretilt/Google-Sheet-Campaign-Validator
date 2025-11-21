#!/bin/bash

# ECR Configuration
ECR_REGISTRY="992382592846.dkr.ecr.us-east-2.amazonaws.com"
ECR_REPOSITORY="trello-lambda-test"
IMAGE_TAG="latest"
AWS_REGION="us-east-2"
SCRIPT_VERSION="1.2.0"

# Colors for Claude Code style output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
GRAY='\033[0;90m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Function to print step headers
print_step() {
    echo -e "${BLUE}${BOLD}$1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}$1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}$1${NC}"
}

# Function to print info messages
print_info() {
    echo -e "${GRAY}$1${NC}"
}

# Function to print version info
print_version() {
    echo -e "${CYAN}${BOLD}ECR Deploy Script v${SCRIPT_VERSION}${NC}"
    echo
    echo -e "${PURPLE}Environment Information:${NC}"
    echo -e "${DIM}┌─ Tool Versions${NC}"

    # Get versions
    DOCKER_VERSION=$(docker --version 2>/dev/null | cut -d' ' -f3 | cut -d',' -f1 || echo "not installed")
    AWS_VERSION=$(aws --version 2>/dev/null | cut -d' ' -f1 | cut -d'/' -f2 || echo "not installed")
    BASH_VERSION=$BASH_VERSION

    echo -e "${DIM}├─ Docker: ${NC}${DOCKER_VERSION}"
    echo -e "${DIM}├─ AWS CLI: ${NC}${AWS_VERSION}"
    echo -e "${DIM}└─ Bash: ${NC}${BASH_VERSION}"
    echo
    echo -e "${PURPLE}Configuration:${NC}"
    echo -e "${DIM}┌─ Deployment Settings${NC}"
    echo -e "${DIM}├─ Registry: ${NC}${ECR_REGISTRY}"
    echo -e "${DIM}├─ Repository: ${NC}${ECR_REPOSITORY}"
    echo -e "${DIM}├─ Tag: ${NC}${IMAGE_TAG}"
    echo -e "${DIM}└─ Region: ${NC}${AWS_REGION}"
    echo
}

# Function to show progress bar
show_progress() {
    local duration=$1
    local message=$2
    echo -ne "${GRAY}${message}${NC}"
    for i in $(seq 1 $duration); do
        echo -ne "${BLUE}.${NC}"
        sleep 0.1
    done
    echo
}

# Function to print fancy header
print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════╗"
    echo "║          ECR Deployment Pipeline         ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to show current deployment status
show_status() {
    echo -e "${CYAN}${BOLD}Current Deployment Status${NC}"
    echo

    # Check if image exists in ECR
    print_step "→ Checking current deployment..."

    # Get current image info
    CURRENT_IMAGE=$(aws ecr describe-images --repository-name $ECR_REPOSITORY --region $AWS_REGION --image-ids imageTag=$IMAGE_TAG --query 'imageDetails[0]' 2>/dev/null)

    if [ $? -eq 0 ] && [ "$CURRENT_IMAGE" != "null" ]; then
        CURRENT_DIGEST=$(echo $CURRENT_IMAGE | jq -r '.imageDigest')
        CURRENT_SIZE=$(echo $CURRENT_IMAGE | jq -r '.imageSizeInBytes')
        CURRENT_PUSHED=$(echo $CURRENT_IMAGE | jq -r '.imagePushedAt')

        # Format size
        FORMATTED_SIZE=$(numfmt --to=iec --suffix=B $CURRENT_SIZE 2>/dev/null || echo "$CURRENT_SIZE bytes")

        print_success "Image found in ECR"
        echo
        echo -e "${PURPLE}Current Image Details:${NC}"
        echo -e "${DIM}┌─ Repository Information${NC}"
        echo -e "${DIM}├─ Repository: ${NC}$ECR_REGISTRY/$ECR_REPOSITORY"
        echo -e "${DIM}├─ Tag: ${NC}$IMAGE_TAG"
        echo -e "${DIM}├─ Digest: ${NC}$CURRENT_DIGEST"
        echo -e "${DIM}├─ Size: ${NC}$FORMATTED_SIZE"
        echo -e "${DIM}└─ Last Push: ${NC}$CURRENT_PUSHED"
        echo

        # Check if there are newer images
        TOTAL_IMAGES=$(aws ecr describe-images --repository-name $ECR_REPOSITORY --region $AWS_REGION --query 'length(imageDetails)' 2>/dev/null)
        if [ "$TOTAL_IMAGES" -gt 1 ]; then
            echo -e "${YELLOW}Found $TOTAL_IMAGES total images in repository${NC}"
        fi
    else
        print_error "No image found with tag '$IMAGE_TAG'"
        echo -e "${GRAY}Run './push.sh' to deploy a new image${NC}"
    fi
}

# Function to show deployment history
show_history() {
    echo -e "${CYAN}${BOLD}Deployment History${NC}"
    echo

    print_step "→ Fetching recent deployments..."

    # Get last 5 images sorted by push date
    RECENT_IMAGES=$(aws ecr describe-images --repository-name $ECR_REPOSITORY --region $AWS_REGION --query 'sort_by(imageDetails, &imagePushedAt) | reverse(@) | [0:5]' 2>/dev/null)

    if [ $? -eq 0 ] && [ "$RECENT_IMAGES" != "[]" ]; then
        echo -e "${PURPLE}Last 5 Deployments:${NC}"
        echo

        # Parse and display each image
        echo "$RECENT_IMAGES" | jq -r '.[] | "\(.imagePushedAt)|\(.imageDigest[7:19])|\(.imageSizeInBytes)|\(.imageTags[0] // "untagged")"' | while IFS='|' read -r date digest size tag; do
            formatted_size=$(numfmt --to=iec --suffix=B $size 2>/dev/null || echo "$size bytes")
            formatted_date=$(date -d "$date" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$date")

            if [ "$tag" == "$IMAGE_TAG" ]; then
                echo -e "${GREEN}● ${BOLD}$tag${NC} ${DIM}($digest) - $formatted_size - $formatted_date${NC}"
            else
                echo -e "${GRAY}● $tag${NC} ${DIM}($digest) - $formatted_size - $formatted_date${NC}"
            fi
        done
    else
        print_error "No deployment history found"
        echo -e "${GRAY}Repository may be empty or inaccessible${NC}"
    fi
}

# Function to show help
show_help() {
    echo -e "${CYAN}${BOLD}ECR Deploy Script${NC}"
    echo
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  ./push.sh [command] [options]"
    echo
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}deploy${NC}        Deploy image to ECR (default action)"
    echo -e "  ${GREEN}status${NC}        Show current deployment status"
    echo -e "  ${GREEN}history${NC}       Show last 5 deployments"
    echo -e "  ${GREEN}version${NC}       Show version and environment info"
    echo -e "  ${GREEN}help${NC}          Show this help message"
    echo
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  --verbose         Enable verbose output (deploy only)"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  ./push.sh                Deploy with default settings"
    echo -e "  ./push.sh deploy --verbose   Deploy with detailed output"
    echo -e "  ./push.sh status             Check current deployment"
    echo -e "  ./push.sh history            View deployment history"
    echo -e "  ./push.sh version            Show environment info"
    echo -e "  ./push.sh help               Show this help"
    echo
}

# Parse command line arguments
COMMAND="deploy"
VERBOSE=false

# First argument is the command
if [ $# -gt 0 ]; then
    case $1 in
        deploy)
            COMMAND="deploy"
            shift
            ;;
        status)
            COMMAND="status"
            shift
            ;;
        history|versions)
            COMMAND="history"
            shift
            ;;
        version|env)
            COMMAND="version"
            shift
            ;;
        help|-h|--help)
            COMMAND="help"
            shift
            ;;
        *)
            # If first arg starts with -, treat as old-style option for backwards compatibility
            if [[ $1 == -* ]]; then
                COMMAND="deploy"
            else
                echo -e "${RED}Unknown command: $1${NC}"
                echo -e "${GRAY}Use './push.sh help' to see available commands${NC}"
                exit 1
            fi
            ;;
    esac
fi

# Parse remaining options
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        -v|--version)
            COMMAND="version"
            shift
            ;;
        -h|--help)
            COMMAND="help"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Execute the requested command
case $COMMAND in
    status)
        show_status
        exit 0
        ;;
    history)
        show_history
        exit 0
        ;;
    version)
        print_version
        exit 0
        ;;
    help)
        show_help
        exit 0
        ;;
    deploy)
        # Continue with deployment below
        ;;
esac

# Show fancy header
print_header

# Show brief version info if verbose
if [ "$VERBOSE" = true ]; then
    print_version
fi

# Step 1: Authenticate Docker to ECR
print_step "→ Authenticating with ECR..."
if [ "$VERBOSE" = true ]; then
    show_progress 5 "  Requesting login token"
fi
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY > /dev/null 2>&1

if [ $? -ne 0 ]; then
    print_error "Failed to authenticate with ECR"
    exit 1
fi
print_success "Successfully authenticated with ECR"
echo

# Step 2: Build Docker image
print_step "→ Building Docker image..."
if [ "$VERBOSE" = true ]; then
    print_info "  Building $ECR_REPOSITORY:$IMAGE_TAG"
    docker build -t $ECR_REPOSITORY:$IMAGE_TAG .
else
    docker build -t $ECR_REPOSITORY:$IMAGE_TAG . > /dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    print_error "Failed to build Docker image"
    exit 1
fi
print_success "Docker image built successfully"
echo

# Step 3: Tag the image for ECR
print_step "→ Tagging image for ECR..."
if [ "$VERBOSE" = true ]; then
    print_info "  Tagging as $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
fi
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

if [ $? -ne 0 ]; then
    print_error "Failed to tag Docker image"
    exit 1
fi
print_success "Image tagged successfully"
echo

# Step 4: Push to ECR
print_step "→ Pushing image to ECR..."
if [ "$VERBOSE" = true ]; then
    show_progress 10 "  Uploading layers"
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
else
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG > /dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    print_error "Failed to push image to ECR"
    exit 1
fi
print_success "Image pushed successfully to ECR"
echo

# Step 5: Get the image digest
print_step "→ Getting image details..."
IMAGE_DIGEST=$(aws ecr describe-images --repository-name $ECR_REPOSITORY --region $AWS_REGION --image-ids imageTag=$IMAGE_TAG --query 'imageDetails[0].imageDigest' --output text)

# Show final results
echo
echo -e "${GREEN}${BOLD}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║           Deployment Complete!        ║${NC}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════╝${NC}"
echo
echo -e "${PURPLE}Deployment Details:${NC}"
echo -e "${DIM}┌─ Image Information${NC}"
echo -e "${DIM}├─ Repository: ${NC}$ECR_REGISTRY/$ECR_REPOSITORY"
echo -e "${DIM}├─ Tag: ${NC}$IMAGE_TAG"
echo -e "${DIM}├─ Digest: ${NC}$IMAGE_DIGEST"
echo -e "${DIM}└─ Full URI: ${NC}$ECR_REGISTRY/$ECR_REPOSITORY@$IMAGE_DIGEST"
echo
echo -e "${YELLOW}${BOLD}Next Steps:${NC}"
echo -e "${GRAY}Update your Lambda function with this command:${NC}"
echo -e "${CYAN}aws lambda update-function-code --function-name YOUR_FUNCTION_NAME --image-uri $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG --region $AWS_REGION${NC}"
echo