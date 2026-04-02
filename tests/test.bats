setup() {
  set -eu -o pipefail
  export BATS_LIB_PATH="${BATS_LIB_PATH:-}:$(brew --prefix)/lib"
  bats_load_library bats-assert
  bats_load_library bats-support
  export DIR="$( cd "$( dirname "$BATS_TEST_FILENAME" )" >/dev/null 2>&1 && pwd )/.."
  export TESTDIR=~/tmp/test-ddev-ai-workspace
  mkdir -p $TESTDIR
  export PROJNAME=test-ddev-ai-workspace
  export DDEV_NON_INTERACTIVE=true
  ddev delete -Oy ${PROJNAME} >/dev/null 2>&1 || true
  cd "${TESTDIR}"
  ddev config --project-name=${PROJNAME}
  ddev start -y >/dev/null
}

health_checks() {
  sleep 15
  # Verify all child add-ons are installed
  run ddev add-on list --installed
  assert_success
  assert_output --partial "ddev-playwright-mcp"
  assert_output --partial "ddev-beads"
  assert_output --partial "ddev-agents-sync"
  assert_output --partial "ddev-opencode"
  assert_output --partial "ddev-claude-code"
  assert_output --partial "ddev-ralph"

  # Verify key containers are running
  run ddev exec -s beads bash -c "echo ok"
  assert_success
  run ddev exec -s agents-sync bash -c "echo ok"
  assert_success

  # Verify host commands are available
  run ddev bd version
  assert_success
}

teardown() {
  set -eu -o pipefail
  cd ${TESTDIR} || ( printf "unable to cd to ${TESTDIR}\n" && exit 1 )
  ddev delete -Oy ${PROJNAME} >/dev/null 2>&1
  [ "${TESTDIR}" != "" ] && rm -rf ${TESTDIR}
}

@test "install from directory" {
  set -eu -o pipefail
  cd ${TESTDIR}
  echo "# ddev add-on get ${DIR} with project ${PROJNAME} in ${TESTDIR} ($(pwd))" >&3
  ddev add-on get ${DIR}
  ddev restart >/dev/null
  health_checks
}

@test "install from release" {
  set -eu -o pipefail
  cd ${TESTDIR} || ( printf "unable to cd to ${TESTDIR}\n" && exit 1 )
  echo "# ddev add-on get trebormc/ddev-ai-workspace with project ${PROJNAME} in ${TESTDIR} ($(pwd))" >&3
  ddev add-on get trebormc/ddev-ai-workspace
  ddev restart >/dev/null
  health_checks
}
