"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Server, RefreshCw, Bot, Wrench } from "lucide-react";
import { api } from "@/lib/api/client";

interface Relic {
  name: string;
  summary: string;
  author: string;
  state: string;
  version?: string;
  deployment?: {
    type?: string;
    port?: number;
    protocol?: string;
    health_check?: string;
  };
  import?: {
    agents?: string[];
    tools?: string[];
  };
  environment?: {
    variables?: Record<string, string>;
  };
}

export default function RelicDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [relic, setRelic] = useState<Relic | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.name) {
      loadRelic(params.name as string);
    }
  }, [params.name]);

  const loadRelic = async (name: string) => {
    try {
      const data = await api.manifests.getRelic(name);
      setRelic(data);
    } catch (error) {
      console.error("Failed to load relic:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!relic) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Relic not found</h2>
          <Button className="mt-4" onClick={() => router.push("/relics")}>
            Back to Relics
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex flex-1 flex-col">
        <Header />
        
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="max-w-5xl mx-auto space-y-6">
            {/* Back Button */}
            <Button variant="ghost" onClick={() => router.push("/relics")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Relics
            </Button>

            {/* Relic Header */}
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <Server className="h-10 w-10 text-primary" />
                  <div>
                    <h1 className="text-3xl font-bold tracking-tight">{relic.name}</h1>
                    {relic.version && (
                      <p className="text-sm text-muted-foreground">v{relic.version}</p>
                    )}
                  </div>
                </div>
                <p className="text-lg text-muted-foreground">{relic.summary}</p>
              </div>
              <div className="flex gap-2">
                <Badge variant={relic.state === "stable" ? "default" : "secondary"} className="text-sm">
                  {relic.state}
                </Badge>
              </div>
            </div>

            <Separator />

            {/* Details Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Basic Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-sm font-medium">Author</div>
                    <div className="text-sm text-muted-foreground">{relic.author || "Unknown"}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">State</div>
                    <div className="text-sm text-muted-foreground capitalize">{relic.state}</div>
                  </div>
                  {relic.version && (
                    <div>
                      <div className="text-sm font-medium">Version</div>
                      <div className="text-sm text-muted-foreground">{relic.version}</div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Deployment Config */}
              {relic.deployment && (
                <Card>
                  <CardHeader>
                    <CardTitle>Deployment Configuration</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {relic.deployment.type && (
                      <div>
                        <div className="text-sm font-medium">Type</div>
                        <div className="text-sm text-muted-foreground capitalize">{relic.deployment.type}</div>
                      </div>
                    )}
                    {relic.deployment.port && (
                      <div>
                        <div className="text-sm font-medium">Port</div>
                        <div className="text-sm text-muted-foreground">{relic.deployment.port}</div>
                      </div>
                    )}
                    {relic.deployment.protocol && (
                      <div>
                        <div className="text-sm font-medium">Protocol</div>
                        <div className="text-sm text-muted-foreground uppercase">{relic.deployment.protocol}</div>
                      </div>
                    )}
                    {relic.deployment.health_check && (
                      <div>
                        <div className="text-sm font-medium">Health Check</div>
                        <div className="text-sm text-muted-foreground font-mono text-xs">
                          {relic.deployment.health_check}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Imports */}
            {relic.import && (
              <Card>
                <CardHeader>
                  <CardTitle>Imported Resources</CardTitle>
                  <CardDescription>Dependencies used by this relic</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {relic.import.agents && relic.import.agents.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="h-4 w-4 text-primary" />
                          <h4 className="text-sm font-medium">Agents ({relic.import.agents.length})</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {relic.import.agents.map((agent: string) => (
                            <Badge key={agent} variant="outline">{agent}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {relic.import.tools && relic.import.tools.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Wrench className="h-4 w-4 text-primary" />
                          <h4 className="text-sm font-medium">Tools ({relic.import.tools.length})</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {relic.import.tools.map((tool: string) => (
                            <Badge key={tool} variant="outline">{tool}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Environment Variables */}
            {relic.environment?.variables && Object.keys(relic.environment.variables).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Environment Variables</CardTitle>
                  <CardDescription>Configuration variables for deployment</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(relic.environment.variables).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center p-2 bg-muted/50 rounded">
                        <code className="text-sm font-semibold">{key}</code>
                        <code className="text-sm text-muted-foreground">{value}</code>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Button disabled title="Coming soon">
                  Deploy Relic
                </Button>
                <Button variant="outline" disabled title="Coming soon">
                  Edit Manifest
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => loadRelic(params.name as string)}
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
