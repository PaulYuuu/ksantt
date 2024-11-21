import (
	"sigs.k8s.io/e2e-framework/pkg/env"
	conf "sigs.k8s.io/e2e-framework/klient/conf"
)

var (
	global env.Environment
)

func TestMain(m *testing.M) {
	// creates a test env with default
	// configuration (i.e. default k8s config)
	global = env.New()
	...
}