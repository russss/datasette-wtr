workflow "New workflow" {
  on = "push"
  resolves = ["Push"]
}

action "Build" {
  uses = "actions/docker/cli@master"
  args = "build -t russss/wtr-api:latest ."
}

action "Deploy filter" {
  needs = ["Build"]
  uses = "actions/bin/filter@master"
  args = "branch master"
}

action "Login" {
  uses = "actions/docker/login@master"
  needs = ["Deploy filter"]
  secrets = ["DOCKER_USERNAME", "DOCKER_PASSWORD"]
}

action "Push" {
  needs = ["Deploy filter", "Login"]
  uses = "actions/docker/cli@master"
  args = "push russss/wtr-api:latest"
}
