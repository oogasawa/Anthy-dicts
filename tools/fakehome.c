// Makes getpwuid and getpwuid_r give $FAKE_HOME as the home directory, so that a library that does not read $HOME
// (Anthy) uses another directory. Used only to measure a trial dictionary without touching the one in use.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <pwd.h>
#include <stdlib.h>
#include <string.h>

struct passwd *getpwuid(uid_t uid) {
    static struct passwd *(*real)(uid_t);
    if (!real) real = dlsym(RTLD_NEXT, "getpwuid");
    struct passwd *p = real(uid);
    const char *home = getenv("FAKE_HOME");
    if (p && home) p->pw_dir = (char *) home;
    return p;
}

int getpwuid_r(uid_t uid, struct passwd *pwd, char *buf, size_t len, struct passwd **result) {
    static int (*real)(uid_t, struct passwd *, char *, size_t, struct passwd **);
    if (!real) real = dlsym(RTLD_NEXT, "getpwuid_r");
    int r = real(uid, pwd, buf, len, result);
    const char *home = getenv("FAKE_HOME");
    if (r == 0 && *result && home) (*result)->pw_dir = (char *) home;
    return r;
}
