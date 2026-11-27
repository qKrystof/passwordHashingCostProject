package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"sort"
	"sync"
	"time"
)

type rec struct {
	tEndUs int64
	latUs  int64
	status int
}

func main() {
	url := flag.String("url", "http://127.0.0.1:3000/login", "target URL")
	method := flag.String("method", "POST", "HTTP method")
	body := flag.String("body", `{"username":"user7","password":"pw-7-dummy"}`, "request body")
	conc := flag.Int("c", 1, "concurrent workers (closed loop)")
	dur := flag.Duration("d", 8*time.Second, "measurement duration")
	warm := flag.Duration("warmup", 2*time.Second, "warm-up duration (not recorded)")
	out := flag.String("out", "", "per-request CSV output path (optional)")
	flag.Parse()

	tr := &http.Transport{
		MaxIdleConns:        *conc * 2,
		MaxIdleConnsPerHost: *conc * 2,
		DialContext:         (&net.Dialer{Timeout: 5 * time.Second}).DialContext,
		DisableCompression:  true,
	}
	client := &http.Client{Transport: tr, Timeout: 60 * time.Second}
	payload := []byte(*body)

	winStart := time.Now().Add(*warm)
	winEnd := winStart.Add(*dur)

	var mu sync.Mutex
	recs := make([]rec, 0, 1<<16)
	var wg sync.WaitGroup
	for w := 0; w < *conc; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			local := make([]rec, 0, 1024)
			for {
				t0 := time.Now()
				if !t0.Before(winEnd) {
					break
				}
				req, _ := http.NewRequest(*method, *url, bytes.NewReader(payload))
				req.Header.Set("Content-Type", "application/json")
				resp, err := client.Do(req)
				status := 0
				if err == nil {
					io.Copy(io.Discard, resp.Body)
					resp.Body.Close()
					status = resp.StatusCode
				}
				t1 := time.Now()
				if !t1.Before(winStart) && t1.Before(winEnd) {
					local = append(local, rec{t1.Sub(winStart).Microseconds(), t1.Sub(t0).Microseconds(), status})
				}
			}
			mu.Lock()
			recs = append(recs, local...)
			mu.Unlock()
		}()
	}
	wg.Wait()

	sort.Slice(recs, func(i, j int) bool { return recs[i].tEndUs < recs[j].tEndUs })
	if *out != "" {
		f, err := os.Create(*out)
		if err != nil {
			panic(err)
		}
		bw := bufio.NewWriter(f)
		fmt.Fprintln(bw, "t_end_us,latency_us,status")
		for _, r := range recs {
			fmt.Fprintf(bw, "%d,%d,%d\n", r.tEndUs, r.latUs, r.status)
		}
		bw.Flush()
		f.Close()
	}

	ok, errs := 0, 0
	lats := make([]float64, 0, len(recs))
	for _, r := range recs {
		if r.status == 200 {
			ok++
			lats = append(lats, float64(r.latUs)/1000)
		} else {
			errs++
		}
	}
	sort.Float64s(lats)
	pct := func(p float64) float64 {
		if len(lats) == 0 {
			return 0
		}
		i := int(p*float64(len(lats))+0.999999) - 1
		if i < 0 {
			i = 0
		}
		if i >= len(lats) {
			i = len(lats) - 1
		}
		return lats[i]
	}
	json.NewEncoder(os.Stdout).Encode(map[string]any{
		"concurrency": *conc, "duration_s": dur.Seconds(), "ok": ok, "errors": errs,
		"rps_ok": float64(ok) / dur.Seconds(),
		"p50_ms": pct(0.50), "p90_ms": pct(0.90), "p99_ms": pct(0.99), "max_ms": pct(1.0),
	})
}
