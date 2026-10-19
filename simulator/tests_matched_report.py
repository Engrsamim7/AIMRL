import numpy as np
from report_matched_gate_study import crossed_samples, bounds


def test_crossed_bootstrap_preserves_exact_constant_effects_and_contrast_pairing():
    a=np.zeros((3,4,2,5,3));a[...,0]=.1;a[...,1]=-.2;a[...,2]=.3
    samples=crossed_samples(a,seed=7,draws=200,chunk=17)
    assert samples.shape==(200,2,3)
    assert np.allclose(samples,np.array([.1,-.2,.3]))
    lo,hi=bounds(samples)
    assert np.allclose(lo,hi) and np.allclose(lo,[[.1,-.2,.3]]*2)


def test_crossed_bootstrap_uses_one_seed_draw_across_all_cases():
    a=np.zeros((3,4,2,5,1))
    a[:,:,0,:,0]=np.arange(4)[None,:,None]
    a[:,:,1,:,0]=-a[:,:,0,:,0]
    samples=crossed_samples(a,seed=13,draws=400,chunk=31)
    assert np.allclose(samples[:,0,0],-samples[:,1,0])
    assert samples[:,0,0].std()>0
    assert np.allclose(samples.mean(axis=1),0.)
