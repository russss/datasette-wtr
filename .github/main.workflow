workflow "New workflow" {
  on = "push"
  resolves = ["Tag"]
}

action "Build" {
  uses = "actions/docker/cli@master"
  args = "build ."
}

action "Login" {
  uses = "actions/docker/login@master"
  needs = ["Build"]
  secrets = ["DOCKER_USERNAME", "DOCKER_PASSWORD"]
}

action "Tag" {
  uses = "actions/docker/tag@8cdf801b322af5f369e00d85e9cf3a7122f49108"
  needs = ["Login"]
  args = "russss/wtr-api:latest"
}

action "Push" {
  needs = ["Tag"]
  uses = "actions/docker/cli@master"
  args = "push russss/wtr-api:latest"
}
