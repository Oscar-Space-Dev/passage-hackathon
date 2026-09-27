class PassageRecorder extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input=inputs[0]?.[0];
    if(input)this.port.postMessage(input.slice().buffer);
    for(const output of outputs)for(const channel of output)channel.fill(0);
    return true;
  }
}
registerProcessor('passage-recorder',PassageRecorder);
